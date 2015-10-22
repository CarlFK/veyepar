#!/usr/bin/env python
#-*- coding: utf-8 *-*

import progressbar


class ProgressFile(file):
    def __init__(self, *args, **kw):
        file.__init__(self, *args, **kw)

        if 'widgets' in kw:
            widgets = kw['widgets']
        else:
            widgets = [
                'Upload: ',
                progressbar.Percentage(), ' ',
                progressbar.Bar(marker=progressbar.RotatingMarker()), ' ', 
                progressbar.ETA(), ' ',
                progressbar.FileTransferSpeed(),
            ]

        self.seek(0, 2)
        self.len = self.tell()
        self.seek(0)

        self.pbar = progressbar.ProgressBar(widgets=widgets, maxval=self.len)
        self.pbar.start()

    @property
    def name(self):
        return super(ProgressFile, self).name
        # return super(ProgressFile, self).name.encode('ascii', 'replace')

    def size(self):
        return self.len

    def __len__(self):
        return self.size()

    def read(self, size=-1):
        if (size > 1e3):
                size = int(1e3)
        try:
            self.pbar.update(self.tell())
            return file.read(self, size)
        finally:
            self.pbar.update(self.tell())
            if self.tell() >= self.len:
                self.pbar.finish()
