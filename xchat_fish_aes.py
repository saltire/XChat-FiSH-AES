
__author__ = "saltire sable <x@saltiresable.com>"
__date__ = "2014-10-15"
__version__ = "3.0"
__module_name__ = 'FiSH_AES'
__module_version__ = '3.0'
__module_description__ = 'FiSH with Blowfish/AES encryption for XChat/HexChat in pure Python'


import hashlib
#import os
#import pickle

try:
    import Crypto.Cipher.Blowfish
    import Crypto.Cipher.AES
except ImportError:
    print "This module requires PyCrypto / The Python Cryptographic Toolkit."
    print "Get it from http://www.dlitz.net/software/pycrypto/."
    raise

import xchat


def sha256(st):
    return hashlib.sha256(st).digest()


def xorstring(a, b, blocksize): # Slow.
    """XOR strings a and b, both of length blocksize."""
    return ''.join(chr(ord(a[i]) ^ ord(b[i])) for i in xrange(blocksize))


class SecretKey:

    def __init__(self, dh=None, text=None):
        self.dh = dh
        self.text = text
        self.hash = ''
        self.aes = False


class KeyMap(dict):

    def _get_real_key(self, target, server):
        server = server.lower()

        target_servers = [s for t, s in self.iterkeys() if t == target]
        target_servers.sort(key=lambda k: len(k), reverse=True)

        # Match the first server that contains the passed server string.
        for s in target_servers:
            if server.rfind(s) >= 0:
                return (target, s)

    def __getitem__(self, ts):
        return dict.__getitem__(self, self._get_real_key(*ts))

    def __contains__(self, ts):
        return dict.__contains__(self, self._get_real_key(*ts))


class FiSH_AES:

    def __init__(self):
        self.keymap = KeyMap()
        self.password = ''

    def set_key(self, word, word_eol, userdata):
        """Save, or display, a key for a particular target on a particular server.
        Defaults to the current channel on the current server."""
        ctx = xchat.get_context()

        target = word[1] if len(word) >= 2 else ctx.get_info('channel')
        server = word[3] if len(word) >= 4 and word[2] == '--network' else ctx.get_info('server')

        try:
            key = self.keymap[target, server]
        except KeyError:
            key = SecretKey()

        if len(word) >= 3 and word[2] != '--network':
            key.text = word_eol[2]
        elif len(word) >= 5 and word[2] == '--network':
            key.text = word_eol[4]
        else:
            if key.text:
                print 'Key for {} @ {} is "{}" (AES: {})'.format(target, server, key.text, key.aes)
            else:
                print 'No key set for {} @ {}'.format(target, server)
            return xchat.EAT_ALL

        key.hash = sha256(key.text)
        self.keymap[target, server] = key

        print 'Key for {} @ {} set to "{}" (AES: {})'.format(target, server, key.text, key.aes)
        return xchat.EAT_ALL

    def unload(self, userdata):
        # FIXME: in the original version, nothing is actually encrypted when saved(!)

#        encrypted_file = os.path.join(xchat.get_info('xchatdir'), 'XChatAES_secure.pickle')
#        if os.path.exists(encrypted_file):
#            return
#
#        tmp_map = KeyMap()
#        for ns, key in self.keymap.iteritems():
#            if key.string:
#                tmp_map[ns] = key
#                key.dh = None
#
#        if self.password:
#            with open(os.path.join(xchat.get_info('xchatdir'), 'XChatAES.pickle'), 'wb') as f:
#                pickle.dump(tmp_map, f)
#                print 'Keys saved to keyfile.'
#        else:
#            print 'No password set; keys not saved to keyfile.'

        print 'XChat-FiSH-AES unloaded successfully.'



fish = FiSH_AES()

xchat.hook_command('key', getattr(fish, 'set_key'),
                   help='show information or set key, /key <nick> [<--network> <network>] [new_key]')

xchat.hook_unload(getattr(fish, 'unload'))

print 'XChat-FiSH-AES loaded successfully.'
