"""
fab <dev|prod|vagrant> <deploy|provision>[:<git ref>]

deploy: deploys the site to the specified environment. If no git ref is provided, deploys HEAD
provision: provisions a box to run the site. is not idempotent. do not rerun.
git ref: a git branch, hash, tag


Example usages:
$ fab vagrant provision
$ fab prod deploy:1.0.1-b7

"""
import datetime, string, random
from os.path import join, dirname, abspath
import fabric.api
from fabric.api import run, task, env, cd, sudo, local
from fabric.contrib.files import sed
from fabtools import require, supervisor, postgres, deb, files
from fabtools.files import upload_template
from fabtools.user import home_directory
import fabtools

env.disable_known_hosts = True
SITE_USER = 'veyepar'
SITE_GROUP = 'veyepar'
SITE_NAME = 'veyepar'
SITE_REPO = 'https://github.com/CarlFK/veyepar.git'
FAB_HOME = dirname(abspath(__file__))

@task
def dev():
    env.update({
        'site': 'veyepar3.nextdayvideo.com',
        'available': 'veyepar',
        'hosts': ['root@veyepar3.nextdayvideo.com'],
        'site_environment': 'dev',
    })


@task
def prod():
    env.update({
        'site': 'veyepar3.nextdayvideo.com',
        'available': 'veyepar',
        'hosts': ['root@veyepar3.nextdayvideo.com'],
        'site_environment': 'prod',
    })


@task
def vagrant():
    env.update({
        'user': 'veyepar',
        'site': '127.0.0.1:2222',
        'available': 'veyepar',
        'hosts': ['ubuntu@127.0.0.1:2222'],
        'site_environment': 'vagrant',
        'key_filename': local('vagrant ssh-config | grep IdentityFile | cut -f4 -d " "', capture=True),
    })


@task
def uname():
    """the hello world of fabric
    """
    fabric.api.require('site', 'available', 'hosts', 'site_environment',
        provided_by=('dev', 'prod', 'vagrant'))
    run('uname -a')


@task
def deploy(version_tag=None):
    """deploys a new version of the site

    version_tag: a git tag, defaults to HEAD
    """
    fabric.api.require('site', 'available', 'hosts', 'site_environment',
        provided_by=('dev', 'prod', 'vagrant'))

    supervisor.stop_process(SITE_NAME)
    new_env = virtualenv_name(commit=version_tag)
    virtualenv = 'veyepar'
    mkvirtualenv(new_env)
    deploy_www_root()
    checkout_repo(commit=version_tag)
    install_site_requirements(virtualenv)
    collectstatic()
    supervisor.start_process(SITE_NAME)


@task
def provision(version_tag=None):
    """Run only once to provision a new host.
    This is not idempotent. Only run once!
    """
    fabric.api.require('site', 'available', 'hosts', 'site_environment',
        provided_by=('dev', 'prod', 'vagrant'))
    install_dependencies()
    # lockdowns()
    setup_postgres()
    if not fabtools.user.exists(SITE_USER):
        sudo('useradd -s/bin/bash -d/home/%s -m %s' % (SITE_USER, SITE_USER))
    deploy_www_root()
    checkout_repo(version_tag)
    setup_django()
    setup_nginx()
    setup_supervisor()


def setup_nginx():
    site_root = join(home_directory(SITE_USER), 'site')
    upload_template('veyepar_nginx',
        '/etc/nginx/sites-available/veyepar',
        context={
            'access_log': join(site_root, 'logs', 'access.log'),
            'error_log': join(site_root, 'logs', 'error.log'),
            'static_location': join(site_root, 'static/'),
            'media_location': join(site_root, 'media/'),
        },
        use_jinja=True, use_sudo=True)
    require.nginx.enabled('veyepar')
    require.nginx.disabled('default')


def setup_supervisor():

    # hacky workaround to ???
    sudo('touch /var/run/supervisor.sock')
    sudo('chmod 777 /var/run/supervisor.sock')
    sudo('service supervisor restart')

    site_root = join(home_directory(SITE_USER), 'site')
    upload_template('veyepar.conf', 
        '/etc/supervisor/conf.d/veyepar.conf',
        context={
            'command': join(site_root, 'bin', 'runserver.sh'),
            'user': SITE_USER,
            'group': SITE_GROUP,
            'logfile': join(site_root, 'logs', 'gunicorn_supervisor.log'),

        },
        use_jinja=True, use_sudo=True)
    supervisor.update_config()


def setup_django(virtualenv='veyepar'):
    mkvirtualenv(virtualenv)
    install_site_requirements(virtualenv)
    install_local_settings()
    syncdb(virtualenv)
    install_dabo(virtualenv)
    collectstatic(virtualenv)


def install_local_settings():
    settings_dir = join(home_directory(SITE_USER), 'site', SITE_NAME, 'dj', 'dj')
    staticdir = join(home_directory(SITE_USER), 'site', 'static')
    with cd(settings_dir):
        upload_template('local_settings.py', 'local_settings.py',
            context={
                'staticdir': staticdir,
                'secret_key': randomstring(32),
            },
            use_jinja=True, use_sudo=True, chown=True, user=SITE_USER)


def install_site_requirements(virtualenv):
    vbin = join(home_directory(SITE_USER), 'venvs', virtualenv, 'bin')
    su('%s/pip install django' % vbin)
    su('%s/pip install djangorestframework' % vbin)
    su('%s/pip install django_extensions' % vbin)
    su('%s/pip install gunicorn' % vbin)
    su('%s/pip install psycopg2' % vbin)

def install_dabo(virtualenv):
    vbin = join(home_directory(SITE_USER), 'venvs', virtualenv, 'bin')
    su('source {}/activate; '.format(vbin) + \
            'cd $(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"); '
            'git clone https://github.com/dabodev/dabo.git dabo-master; '
            'ln -sf dabo-master/dabo' )

def collectstatic(site_version):
    vbin = join(home_directory(SITE_USER), 'venvs', site_version, 'bin')
    staticdir = join(home_directory(SITE_USER), 'site', 'static')
    djangodir = join(home_directory(SITE_USER), 'site', SITE_NAME, 'dj')
    with cd(djangodir):
        su('source %s/activate; ./manage.py collectstatic --noinput --clear' % vbin)
    su('chmod -R a+rx %s' % staticdir)


def syncdb(site_version):
    vbin = join(home_directory(SITE_USER), 'venvs', site_version, 'bin')
    djangodir = join(home_directory(SITE_USER), 'site', SITE_NAME, 'dj')
    with cd(djangodir):
        su('source %s/activate; ./manage.py migrate --noinput' % vbin)


def deploy_www_root():
    site_root = join(home_directory(SITE_USER), 'site')
    site_home = home_directory(SITE_USER)
    bindir = join(site_root, 'bin')

    with cd(home_directory(SITE_USER)):
        su('mkdir -p venvs site')

    with cd(site_root):
        su('mkdir -p logs bin env static')
        upload_template('runserver.sh', 
            join(bindir, 'runserver.sh'),
            context={
                'site_version': 'veyepar',
                'site_home': site_home,
                'site_name': SITE_USER,
                'django_dir': join(SITE_NAME, 'dj'),
                'wsgi_module': 'dj.wsgi',
                'django_settings_module': 'dj.settings',
            },
            use_jinja=True, use_sudo=True, chown=True, user=SITE_USER)

    with cd(bindir):
        su('chmod +x runserver.sh')


def setup_postgres():
    require.postgres.server()
    # NOTE: fabtools.require.postgres.user did not allow me to create a user with no pw
    if not postgres.user_exists(SITE_USER):
        su('createuser -S -D -R -w %s' % SITE_USER, 'postgres')
    if not postgres.database_exists(SITE_USER):
        require.postgres.database(SITE_USER, SITE_USER, encoding='UTF8', locale='en_US.UTF-8')
    # TODO change default port
    # port = '5%s' % ''.join(random.choice(string.digits) for x in range(4))
    #sed('/etc/postgresql/9.1/main/postgresql.conf', 'port = 5432', 'port = %s' % port) 

def lockdowns():
    # don't share nginx version in header and error pages
    sed('/etc/nginx/nginx.conf', '# server_tokens off;', 'server_tokens off;', use_sudo=True)
    # require keyfile authentication
    sed('/etc/ssh/sshd_config', '^#PasswordAuthentication yes', 'PasswordAuthentication no', use_sudo=True)


def install_dependencies():
    require.deb.uptodate_index(max_age={'hour': 1})
    add_apt_sources()
    install_debian_packages()
    install_python_packages()


def add_apt_sources():
    deb.add_apt_key(url='http://www.rabbitmq.com/rabbitmq-signing-key-public.asc')
    require.deb.source('rabbitmq-server', 'http://www.rabbitmq.com/debian/', 'testing', 'main')
    require.deb.uptodate_index(max_age={'hour': 1})


def install_debian_packages():
    require.deb.packages([
        'python-software-properties',
        'python-dev',
        'build-essential',
        'python-reportlab',
        'python-imaging',
        'nginx-extras',
        #'libxslt1-dev',
        'supervisor',
        'git',
        'postgresql',
        'python-psycopg2',
        'curl',
        'vim',
        'tmux',
        'htop',
        'tig',
        'ack-grep',
        'python3-pip',
    ])

    sudo('apt build-dep -y psycopg2')


def install_python_packages():

    # install global python packages
    require.python.packages([
        'virtualenvwrapper',
        'setproctitle',
    ], use_sudo=True)


def su(cmd, user=None):
    if user is None:
        user = SITE_USER
    sudo("su %s -c '%s'" % (user, cmd))


def checkout_repo(commit=None):
    site_root = join(home_directory(SITE_USER), 'site')
    repodir = join(site_root, SITE_NAME)
    if not files.is_dir(repodir):
        with cd(site_root):
            su('git clone %s %s' % (SITE_REPO, SITE_NAME))
    with cd(repodir):
        su('git fetch')
        if commit is None:
            commit = 'origin/master'
        su('git checkout %s' % commit)


def randomstring(n):
    return ''.join(random.choice(string.ascii_letters + string.digits + '~@#%^&*-_') for x in range(n))


def virtualenv_name(commit=None):
    if commit is None:
        repodir = join(home_directory(SITE_USER), 'site', SITE_NAME)
        with cd(repodir):
            commit = run('git rev-parse HEAD').strip()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    return '%s-%s' % (timestamp, commit)


def mkvirtualenv(virtualenv):
    with cd(join(home_directory(SITE_USER), 'venvs')):
        su('virtualenv --python=python3.5 --system-site-packages %s' % virtualenv)

