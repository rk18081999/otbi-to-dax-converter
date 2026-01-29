SELECT DISTINCT
    /* Customer / Party */
    hp.PARTY_NUMBER        AS CUSTOMER_NUMBER,
    hp.PARTY_NAME          AS CUSTOMER_NAME,
    hp.COUNTY              AS COUNTY,

    /* Customer Account */
    hca.ACCOUNT_NUMBER     AS CUSTOMER_ACCOUNT_NUMBER,
    hca.ACCOUNT_NAME       AS CUSTOMER_ACCOUNT_NAME,
    hca.STATUS             AS ACCOUNT_STATUS_CODE,

    /* Lookup decode */
    flv.MEANING            AS ACCOUNT_STATUS

FROM HZ_CUST_ACCOUNTS hca

/* Account Sites (SetID context – required by OTBI logic) */
LEFT JOIN HZ_CUST_ACCT_SITES_ALL hcas
    ON hca.CUST_ACCOUNT_ID = hcas.CUST_ACCOUNT_ID

LEFT JOIN FND_SETID_SETS_VL fss
    ON hcas.SET_ID = fss.SET_ID

/* Party information */
LEFT JOIN HZ_PARTIES hp
    ON hca.PARTY_ID = hp.PARTY_ID

/* Account Status lookup */
LEFT JOIN FND_LOOKUP_VALUES_TL flv
    ON hca.STATUS = flv.LOOKUP_CODE
   AND flv.LOOKUP_TYPE = 'CODE_STATUS'
   AND flv.LANGUAGE = 'US'
   AND flv.VIEW_APPLICATION_ID = 0
   AND flv.SET_ID = 0

/* OTBI filter */
WHERE hp.COUNTY = 'FAIRFAX'

/* OTBI ordering (matches logical ORDER BY) */
ORDER BY
    CUSTOMER_NUMBER,
    CUSTOMER_NAME,
    CUSTOMER_ACCOUNT_NUMBER,
    CUSTOMER_ACCOUNT_NAME,
    ACCOUNT_STATUS_CODE,
    ACCOUNT_STATUS,
    COUNTY;