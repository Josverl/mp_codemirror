// Stub for 'tmp' module — provides no-op implementations for browser
module.exports = {
    setGracefulCleanup: function() {},
    fileSync: function() { return { name: '/tmp/stub', fd: -1, removeCallback: function() {} }; },
    dirSync: function() { return { name: '/tmp/stub', removeCallback: function() {} }; },
    tmpNameSync: function() { return '/tmp/stub'; },
};
