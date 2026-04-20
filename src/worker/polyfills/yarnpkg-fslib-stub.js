// Stubs for @yarnpkg/fslib — provides minimal class stubs for browser
// Pyright's realFileSystem.ts extends ZipOpenFS; we need a valid base class.

class FakeFS {}
class BasePortableFakeFS extends FakeFS {}
class ZipOpenFS extends BasePortableFakeFS {}
class NodeFS extends BasePortableFakeFS {}
class PosixFS extends BasePortableFakeFS {}
class VirtualFS extends BasePortableFakeFS {}
class ZipFS extends BasePortableFakeFS {}
class CwdFS extends BasePortableFakeFS {}
class JailFS extends BasePortableFakeFS {}
class LazyFS extends BasePortableFakeFS {}
class ProxiedFS extends BasePortableFakeFS {}
class AliasFS extends BasePortableFakeFS {}
class NoFS extends BasePortableFakeFS {}
class MountFS extends BasePortableFakeFS {}

const ppath = {
    join: (...args) => args.join('/'),
    resolve: (...args) => args.join('/'),
    dirname: (p) => p.split('/').slice(0, -1).join('/'),
    basename: (p) => p.split('/').pop(),
};
const npath = ppath;

module.exports = {
    FakeFS,
    BasePortableFakeFS,
    ZipOpenFS,
    NodeFS,
    PosixFS,
    VirtualFS,
    ZipFS,
    CwdFS,
    JailFS,
    LazyFS,
    ProxiedFS,
    AliasFS,
    NoFS,
    MountFS,
    ppath,
    npath,
    PortablePath: '',
    Filename: '',
    NativePath: '',
    constants: {},
    errors: {},
    statUtils: {},
};
