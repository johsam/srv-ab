/*
 *  Created by: Johan S - 2017
 *
 */

// @flow

Ext.define('Josa.base.window', {
    extend: 'Ext.Window',
    alias: 'josa.base.window',

    title: 'Base Window',
    //iconCls : 'icon-puppet',
    layout: 'fit',

    hidden: true,
    plain: true,
    border: true,

    buttonAlign: 'center',
    minButtonWidth: 120,

    height: 100,
    width: 100,

    closable: false,
    maximizable: true,
    closeAction: 'hide',

    /*******************************************************************
     *
     *  initComponent
     *
     ******************************************************************/

    initComponent: function () {
        this.callParent(arguments);
        //console.log('Shb.base.window->initComponent->',this.title);
    },
});
