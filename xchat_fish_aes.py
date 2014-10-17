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

    def __init__(self, dh=None, text=''):
        self.dh = dh
        self.text = text
        self.hash = ''
        self.aes = False

    def set_text(self, text=''):
        self.text = text
        self.hash = sha256(text)

    def get_type(self):
        return 'AES' if self.aes else 'Blowfish'


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
        target = xchat.get_info('channel')
        server = xchat.get_info('server')
        newkey = ''

        if len(word) == 2:
            newkey = word[1]
        elif len(word) >= 3:
            if word[1][0] == ':':
                newkey = word_eol[1][1:]
            else:
                target = word[1]
                if len(word) == 3:
                    newkey = word[2]
                else:
                    if word[2][0] == ':':
                        newkey = word_eol[2][1:]
                    else:
                        server = word[2]
                        newkey = word_eol[3]

        try:
            key = self.keymap[target, server]
        except KeyError:
            key = SecretKey()
            self.keymap[target, server] = key

        if newkey:
            key.set_text(newkey)
            print 'Key for {} @ {} set to "{}" ({}).'.format(target, server, key.text,
                                                             key.get_type())
        elif key.text:
            print 'Key for {} @ {} is "{}" ({}).'.format(target, server, key.text, key.get_type())
        else:
            print 'No key set for {} @ {}.'.format(target, server)

        return xchat.EAT_ALL

    def set_key_type(self, word, word_eol, userdata):
        target = xchat.get_info('channel')
        server = xchat.get_info('server')
        ktype = ''

        if len(word) == 2:
            ktype = word[1]
        elif len(word) >= 3:
            target = word[1]
            if len(word) == 3:
                ktype = word[2]
            else:
                server = word[2]
                ktype = word[3]

        try:
            key = self.keymap[target, server]
        except KeyError:
            print 'No key set for {} @ {}.'.format(target, server)
        else:
            if ktype.lower() in ['aes', 'a', 'blowfish', 'b']:
                key.aes = (ktype.lower() in ['aes', 'a'])
                print 'Key type for {} @ {} set to {}.'.format(target, server, key.get_type())
            elif not ktype:
                print 'Key type for {} @ {} is {}.'.format(target, server, key.get_type())
            else:
                print 'Key type must be either AES or Blowfish.'

        return xchat.EAT_ALL

    def list_keys(self, word, word_eol, userdata):
        """List all currently known keys."""
        n = len(self.keymap)
        print 'Found {} key{}.'.format(n, '' if n == 1 else 's')
        for (target, server), key in self.keymap.iteritems():
            print '  {} @ {}: {} ({})'.format(target, server, key.text, key.get_type())
        return xchat.EAT_ALL

    def remove_key(self, word, word_eol, userdata):
        target = word[1] if len(word) >= 2 else xchat.get_info('channel')
        server = word[2] if len(word) >= 3 else xchat.get_info('server')

        try:
            del self.keymap[target, server]
            print 'Key removed for {} @ {}.'.format(target, server)
        except KeyError:
            print 'No key found for {} @ {}.'.format(target, server)

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
                   help=('/KEY [<nick/channel>] [<network>] [new_key],'
                         'display or set the key for a particular nick or channel.'))
xchat.hook_command('key_list', getattr(fish, 'list_keys'),
                   help='/KEY_LIST, list all currently known keys.')
xchat.hook_command('key_remove', getattr(fish, 'remove_key'),
                   help='/KEY_REMOVE [<nick/channel>] [<network>], remove a key.')
xchat.hook_command('key_type', getattr(fish, 'set_key_type'),
                   help=('/KEY_TYPE [<nick/channel>] [<network>] [AES|Blowfish],'
                         'display or set the key type for a particular nick or channel.'))


xchat.hook_unload(getattr(fish, 'unload'))

print 'XChat-FiSH-AES loaded successfully.'
