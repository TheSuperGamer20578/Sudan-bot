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
