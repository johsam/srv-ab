/*
 *  Created by: Johan S - 2017
 *
 *
 */

/* global abConfig:true */

// @flow

Ext.onReady(function () {
    delete Ext.tip.Tip.prototype.minWidth;

    Ext.override(Ext.tip.Tip, {
        componentLayout: {
            type: 'fieldset',
            getDockedItems: function () {
                return [];
            },
        },
    });

    Ext.QuickTips.init();

    Ext.apply(Ext.QuickTips.getQuickTip(), {
        maxWidth: 800,
        // minWidth: 500
    });

    // Start create stuff

    const josaDocHeight = Ext.getBody().getViewSize().height;
    const josaDocWidth = Ext.getBody().getViewSize().width;

    const abGrid = Ext.create('Josa.ab.grid', {});

    const abWindow = Ext.create('josa.base.window', {
        title: 'Please wait...',
        x: abConfig.settings.winMargin,
        y: abConfig.settings.winMargin,
        width: josaDocWidth - 2 * abConfig.settings.winMargin,
        height: josaDocHeight - 2 * abConfig.settings.winMargin,

        items: [abGrid],

        buttons: [
            {
                text: 'Reload',
                handler: function () {
                    abGrid.getStore().load();
                },
            },
        ],

        /*******************************************************************
         *
         *  onShowEvent
         *
         ******************************************************************/

        onShowEvent: function (_c, _o) {
            const store = abGrid.getStore();
            store.load();
        },
    });

    const abGridStoreLoad = (store, _records, _success) => {
        abWindow.setTitle(store.getTotalCount() + ' audio book(s) loaded');
        abWindow.down('textfield[name=searchField]').focus(true, true);
    };

    abWindow.on('show', abWindow.onShowEvent, this);
    abGrid.getStore().on('load', abGridStoreLoad, this);

    abWindow.show();
});
