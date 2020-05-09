/*
 *  Created by: Johan S - 2017
 *
 */

// @flow

Ext.define('Josa.Utilities', {
    statics: {
        /*******************************************************************
         *
         * Function -> prettyBytes
         *
         ******************************************************************/

        bytes: function (v) {
            /*eslint no-bitwise: "off"*/
            const e = (Math.log(v) / Math.log(1024)) | 0;
            return +(v / 1024 ** e).toFixed(1) + ' ' + ('kMGTPEZY'[e - 1] || '') + 'B';
        },

        prettyBytes: function (size, nospace, one) {
            const sizes = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB'];

            let mysize;
            let g;
            let s;
            let fxd;

            sizes.forEach((f, id) => {
                if (one) {
                    g = f.slice(0, 1);
                }

                s = 1024 ** id;

                if (size >= s) {
                    fxd = String((size / s).toFixed(1));

                    if (fxd.indexOf('.0') === fxd.length - 2) {
                        fxd = fxd.slice(0, -2);
                    }
                    mysize = fxd + (nospace ? '' : ' ') + f;
                }
            });

            // Zero handling
            // Always prints in Bytes

            if (!mysize) {
                g = one ? sizes[0].slice(0, 1) : sizes[0];
                mysize = '0' + (nospace ? '' : ' ') + g;
            }

            return mysize;
        },
    },
});
