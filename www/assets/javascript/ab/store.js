/*
 *  Created by: Johan S - 2017
 *
 *
 */

/* global abConfig:true Josa:true */

// @flow

Ext.define('Josa.ab.storemodel', {
    extend: 'Ext.data.Model',
    fields: [
        { name: 'file_timestamp', type: 'string' },
        { name: 'file_size', type: 'int' },
        'mp3_author',
        'mp3_album',
        { name: 'mp3_year', type: 'int' },
        'mp3_narrator',
        'rar_albumart_name',
        'rar_albumart',
        { name: 'rar_mp3_files', type: 'int' },
        'rar_albumart',
        'rar_albumart_size',
        'rar_mp3_duration',
        'rar_mp3_artist',
        'rar_mp3_genre',
        { name: 'rar_other_files', type: 'int' },
        'rar_other_list',
    ],
});

Ext.define('Josa.ab.store', {
    extend: 'Ext.data.Store',
    alias: 'josa.ab.store',
    model: Josa.ab.storemodel,

    config: {},

    proxy: {
        type: 'ajax',
        url: abConfig.settings.urls.ab,
        simpleSortMode: true,
        reader: {
            type: 'json',
            root: 'rows',
            totalProperty: 'totalcount',
        },
    },

    autoLoad: false,
    remoteSort: false,

    sorters: [{ property: 'mp3_author', direction: 'ASC' }],

    groupField: 'mp3_author',

    /*******************************************************************
    *
    * Event -> onbeforeLoad
    *
    ******************************************************************/

    onbeforeLoad: function() {},

    /******************************************************************
    *
    * constructor
    *
    ******************************************************************/

    constructor: function() {
        this.callParent(arguments);
        this.on('beforeLoad', this.onbeforeLoad, this);
    },
});
