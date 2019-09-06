# -*- coding: utf-8 -*-
#
#  libgencmd.py
#  
#  Copyright (c) 2019 Tom van Leeuwen
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# This is a simple wrapper around the C functions used by vcgencmd.
# The initialization sequence is a port from the "gencmd.c" file
# from the Raspberry Pi userland application source, the actual vc_gencmd
# function is a direct wrapper around the C function.
#
# The structure pointers do not have any structure information because
# it is all handled by the C functions.
#

import os
import ctypes

class VcGenCMD():
    
    # Just allocate one page for the result.
    buf_size = 4096
    
    def __init__(self):
        # Both vchi and vchi_connections are pointers to objects that are
        # allocated by the C libraries. We don't care about their types.
        self.vchi = ctypes.pointer(ctypes.c_void_p())
        self.vchi_connections = ctypes.pointer(ctypes.c_void_p())
        
        self._clib = ctypes.CDLL("libbcm_host.so", use_errno = True)
        self._clib.vcos_init.argtypes = []
        self._clib.vchi_initialise.argtypes = [ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))]
        self._clib.vchi_connect.argtypes = [ctypes.POINTER(None), ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
        self._clib.vc_vchi_gencmd_init.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)), ctypes.c_int]
        self._clib.vc_gencmd.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_size_t, ctypes.POINTER(ctypes.c_char)]
        
        # C code does not check for success either.
        _ = self._clib.vcos_init()
        
        if self._clib.vchi_initialise(ctypes.pointer(self.vchi)) != 0:
            errno = ctypes.get_errno()
            raise IOError(errno, os.strerror(errno))
        
        if self._clib.vchi_connect(None, 0, self.vchi) != 0:
            errno = ctypes.get_errno()
            raise IOError(errno, os.strerror(errno))
        
        # Again, C code does not check for success here either.
        self._clib.vc_vchi_gencmd_init(self.vchi, ctypes.pointer(self.vchi_connections), ctypes.c_int(1))

    def vc_gencmd(self, command):
        """ Sends the command to the VideoCore and returns the result.
        
            @param command  Byte-array containing the command (ASCII)
            
            @return byte-array containing the result.
        """
        command_c = ctypes.create_string_buffer(command)
        response = ctypes.create_string_buffer(self.buf_size)
        
        if self._clib.vc_gencmd(response, ctypes.c_size_t(self.buf_size), command_c) != 0:
            errno = ctypes.get_errno()
            raise IOError(errno, os.strerror(errno))

        return response.value
