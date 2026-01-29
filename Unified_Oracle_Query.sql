WITH 
SAWITH0 AS (select  /*+ inline */  T2224764.C309398529 as c3,
     T2224764.C69081989 as c4,
     T2224764.C254160071 as c5,
     T2224764.C310524679 as c6,
     T2224764.C160744894 as c7,
     T2224764.C123057362 as c8
from 
     (SELECT V131818700.ACCOUNT_NAME AS C309398529,         V131818700.ACCOUNT_NUMBER AS C69081989,         V390585951.COUNTY AS C254160071,         V390585951.PARTY_NAME AS C310524679,         V390585951.PARTY_NUMBER AS C160744894,         V131818700.ACCOUNT_STATUS AS C123057362,         V131818700.CUST_ACCT_ID AS C306970227,         V390585951.PARTY_ID AS PKA_PartyId0 FROM (SELECT CustomerAccount.ACCOUNT_NAME,         CustomerAccount.ACCOUNT_NUMBER,         CustomerAccount.CUST_ACCOUNT_ID AS CUST_ACCT_ID,         CustomerAccount.PARTY_ID AS ACCOUNT_PARTY_ID,         CustomerAccount.STATUS AS ACCOUNT_STATUS,         CustomerAccountSite.SET_ID AS CustomerAccountSite_SET_ID FROM HZ_CUST_ACCOUNTS CustomerAccount, HZ_CUST_ACCT_SITES_ALL CustomerAccountSite, FND_SETID_SETS_VL SetIdSet WHERE ((CustomerAccount.CUST_ACCOUNT_ID = CustomerAccountSite.CUST_ACCOUNT_ID(+) AND CustomerAccountSite.SET_ID = SetIdSet.SET_ID(+)) AND ( (1=1) AND (1=1))) AND ((1=1))) V131818700, (SELECT /*+ qb_name(CustomerPVO) */ CustomerPartyPEO.COUNTY,         CustomerPartyPEO.PARTY_ID,         CustomerPartyPEO.PARTY_NAME,         CustomerPartyPEO.PARTY_NUMBER FROM HZ_PARTIES CustomerPartyPEO) V390585951 WHERE (V131818700.ACCOUNT_PARTY_ID = V390585951.PARTY_ID(+)) AND ( ( (V390585951.COUNTY = 'FAIRFAX' ) ) )) T2224764),
SAWITH1 AS (select  /*+ inline */  T2224765.C389230568 as c1,
     T2224765.C164164071 as c2
from 
     (SELECT V72673585.MEANING AS C389230568,         V72673585.LOOKUP_CODE AS C164164071,         V72673585.LANGUAGE AS C343259318,         V72673585.LOOKUP_TYPE AS C417433804,         V72673585.VIEW_APPLICATION_ID AS C456636657,         V72673585.SET_ID AS C497682495 FROM FND_LOOKUP_VALUES_TL V72673585 WHERE ( ( (V72673585.LOOKUP_TYPE = 'CODE_STATUS' ) )  AND ( (V72673585.VIEW_APPLICATION_ID = 0 ) )  AND ( (V72673585.SET_ID = 0 ) )  AND ( (V72673585.LANGUAGE = 'US' ) ) )) T2224765),
SAWITH2 AS (select  /*+ inline */  D2.c1 as c2,
     D1.c8 as c3,
     D1.c3 as c4,
     D1.c4 as c5,
     D1.c5 as c6,
     D1.c6 as c7,
     D1.c7 as c8
from 
     
          SAWITH0 D1 left outer join SAWITH1 D2 On D1.c8 = D2.c2),
SAWITH3 AS (select  /*+ inline */  nvl(D901.c2 , D901.c3) as c2,
     D901.c4 as c3,
     D901.c5 as c4,
     D901.c6 as c5,
     D901.c7 as c6,
     D901.c8 as c7,
     D901.c3 as c8
from 
     SAWITH2 D901)
select distinct D1.c7 as c7,
     D1.c6 as c6,
     D1.c4 as c4,
     D1.c3 as c3,
     D1.c2 as c2,
     D1.c8 as c8,
     D1.c5 as c5,
     0 as c1
from 
     SAWITH3 D1
order by c3, c4, c5, c6, c7, c8

]]