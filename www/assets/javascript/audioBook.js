/*
 *  Created by: Johan S - 2017
 *
 *
 */

/* jshint trailing: true ,  sub:true */
/* global abConfig:true */

// @flow

Ext.onReady(function() {
    delete Ext.tip.Tip.prototype.minWidth;

    Ext.override(Ext.tip.Tip, {
        componentLayout: {
            type: 'fieldset',
            getDockedItems: function() {
                return [];
            },
        },
    });

    Ext.QuickTips.init();

    Ext.apply(Ext.QuickTips.getQuickTip(), {
        maxWidth: 800,
        // minWidth: 500
    });

    var abWindow;

    /*eslint no-unused-vars: ["error", {"args": "none"}]*/
    function abGridStoreLoad(store, records, success) {
        abWindow.setTitle(store.getTotalCount() + ' audio book(s) loaded');
        abWindow.down('textfield[name=searchField]').focus(true, true);
    }

    // Start create stuff

    var josaDocHeight = Ext.getBody().getViewSize().height;
    var josaDocWidth = Ext.getBody().getViewSize().width;

    var abGrid = Ext.create('Josa.ab.grid', {});

    abWindow = Ext.create('josa.base.window', {
        title: 'Please wait...',
        x: abConfig.settings.winMargin,
        y: abConfig.settings.winMargin,
        width: josaDocWidth - 2 * abConfig.settings.winMargin,
        height: josaDocHeight - 2 * abConfig.settings.winMargin,

        items: [abGrid],

        buttons: [
            {
                text: 'Reload',
                handler: function() {
                    abGrid.getStore().load();
                },
            },
        ],

        /*******************************************************************
        *
        *  onShowEvent
        *
        ******************************************************************/

        onShowEvent: function(c, o) {
            var store = abGrid.getStore();
            store.load();
        },
    });

    abWindow.on('show', abWindow.onShowEvent, this);
    abGrid.getStore().on('load', abGridStoreLoad, this);

    abWindow.show();
});
