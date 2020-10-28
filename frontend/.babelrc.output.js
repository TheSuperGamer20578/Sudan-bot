// TODO: configure Babel for output
// For Babel Rollup output plugin

module.exports = {
    presets: [
        [
            '@babel/env',
            {
                targets: {
                    edge: 12,
                    firefox: 18,
                    chrome: 24,
                    safari: 5
                }
            }
        ]
    ]
};
