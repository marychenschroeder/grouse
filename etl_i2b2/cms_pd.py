"""cms_pd -- CMS ETL using pandas (WIP)

As detailed in the example log below, the steps of an `DataLoadTask` are:

 - Allocate an upload_id and insert an upload_status record
 - Connect and select a rows from the input table bounded by bene_id;
   logging the execution plan first.
 - For each chunk of several thousand of such rows:
   - stack diagnoses and pivot facts
   - map patients and encounters
   - bulk insert into observation_fact_N where N is the upload_id

17:37:02 INFO 0:00:00 [1] upload job: <oracle://me@db-server/sgrouse>...
17:37:02 INFO 0:00:00.002542 [1, 2] scalar select I2B2.sq_uploadstatus_uploadid.nextval...
1720 for CarrierClaimUpload #1 of 64; 121712 bene_ids
17:37:02 INFO 0:00:00.005157 [1, 2] scalar select I2B2.sq_uploadstatus_uploadid.nextval.
17:37:02 INFO 0:00:00.010149 [1, 3] execute INSERT INTO "I2B2".upload_status (upload_id, upload_label, user_id, source_cd, load_date, transform_name) VALUES (:upload_id, :upload_label, :user_id, :source_cd, now(), :transform_name)...
17:37:02 INFO 0:00:00.003866 [1, 3] execute INSERT INTO "I2B2".upload_status (upload_id, upload_label, user_id, source_cd, load_date, transform_name) VALUES (:upload_id, :upload_label, :user_id, :source_cd, now(), :transform_name).
17:37:02 INFO  1720 for CarrierClaimUpload #-1 of -1; 121712 bene_ids 1...
17:37:02 INFO 0:00:00.042701 [1, 4] UP#1720: ETL chunk from CMS_DEID.bcarrier_claims...
17:37:02 INFO 0:00:00.043673 [1, 4, 5] get facts...
17:37:02 INFO 0:00:00.196869 [1, 4, 5, 6] execute explain plan for SELECT * ...
17:37:02 INFO 0:00:00.007902 [1, 4, 5, 6] execute explain plan for SELECT * .
17:37:02 INFO 0:00:00.205344 [1, 4, 5, 7] execute SELECT PLAN_TABLE_OUTPUT line FROM TABLE(DBMS_XPLAN.DISPLAY())...
17:37:02 INFO 0:00:00.013324 [1, 4, 5, 7] execute SELECT PLAN_TABLE_OUTPUT line FROM TABLE(DBMS_XPLAN.DISPLAY()).
17:37:02 INFO get chunk [1031320, 1]
query: SELECT *
WHERE "CMS_DEID".bcarrier_claims.bene_id BETWEEN :bene_id_1 AND :bene_id_2 plan:
Plan hash value: 2999476641
 
---------------------------------------------------------------------------------------------------------------------
| Id  | Operation                            | Name                | Rows  | Bytes | Cost (%CPU)| Time     | Inst   |
---------------------------------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT REMOTE              |                     |  1113K|   199M|  2013K  (1)| 00:01:19 |        |
|*  1 |  FILTER                              |                     |       |       |            |          |        |
|   2 |   TABLE ACCESS BY INDEX ROWID BATCHED| BCARRIER_CLAIMS     |  1113K|   199M|  2013K  (1)| 00:01:19 | SGROU~ |
|*  3 |    INDEX RANGE SCAN                  | CMS_IX_BCACLA_BENID |  2009K|       |  5406   (1)| 00:00:01 | SGROU~ |
---------------------------------------------------------------------------------------------------------------------
 
Predicate Information (identified by operation id):
---------------------------------------------------
 
   1 - filter(:BENE_ID_2>=:BENE_ID_1)
   3 - access("BCARRIER_CLAIMS"."BENE_ID">=:BENE_ID_1 AND "BCARRIER_CLAIMS"."BENE_ID"<=:BENE_ID_2)
 
Note
-----
   - fully remote statement

17:37:02 INFO 0:00:00.224509 [1, 4, 5, 8] UP#1720: select from CMS_DEID.bcarrier_claims...
17:37:09 INFO 0:00:06.749958 [1, 4, 5, 8] UP#1720: select from CMS_DEID.bcarrier_claims + 100000 rows = 100000 for 1399 (1.15%) of 121712 bene_ids.
17:37:09 INFO 0:00:06.975701 [1, 4, 5, 9] stack diagnoses from 100000 CMS_DEID.bcarrier_claims records...
17:37:12 INFO 0:00:02.963609 [1, 4, 5, 9] stack diagnoses from 100000 CMS_DEID.bcarrier_claims records 333580 diagnoses.
17:37:12 INFO 0:00:09.940432 [1, 4, 5, 10] pivot facts from 100000 CMS_DEID.bcarrier_claims records...
17:37:22 INFO 0:00:10.808200 [1, 4, 5, 10] pivot facts from 100000 CMS_DEID.bcarrier_claims records 2767740 total observations.
17:37:23 INFO 0:00:21.472786 [1, 4, 5, 11] mapping 2767740 facts...
17:37:23 INFO 0:00:21.474279 [1, 4, 5, 11, 12] read_sql select patient_ide bene_id, patient_num from I2B2.patient_mapping
{'bene_id_last': '1001496', 'bene_id_first': '1', 'patient_ide_source': 'ccwdata.org(BENE_ID)'}...
17:37:23 INFO 0:00:00.315361 [1, 4, 5, 11, 12] read_sql select patient_ide bene_id, patient_num from I2B2.patient_mapping
{'bene_id_last': '1001496', 'bene_id_first': '1', 'patient_ide_source': 'ccwdata.org(BENE_ID)'}.
17:37:24 INFO 0:00:22.876878 [1, 4, 5, 11, 13] read_sql select medpar.medpar_id, medpar.bene_id, emap.encounter_num
{'bene_id_last': '1001496', 'bene_id_first': '1', 'encounter_ide_source': 'ccwdata.org(MEDPAR_ID)'}...
17:37:25 INFO 0:00:00.389943 [1, 4, 5, 11, 13] read_sql select medpar.medpar_id, medpar.bene_id, emap.encounter_num
{'bene_id_last': '1001496', 'bene_id_first': '1', 'encounter_ide_source': 'ccwdata.org(MEDPAR_ID)'}.
17:37:41 INFO 0:00:17.737663 [1, 4, 5, 11] mapping 2767740 facts pmap: 16627 emap: 2121.
17:37:43 INFO 0:00:40.980482 [1, 4, 5] get facts 2767740 facts.
17:37:43 INFO 0:00:41.025014 [1, 4, 14] UP#1720: bulk insert 2767740 rows into observation_fact_1720...
17:38:17 INFO 0:00:34.165037 [1, 4, 14] UP#1720: bulk insert 2767740 rows into observation_fact_1720.
17:38:17 INFO 0:01:15.148141 [1, 4] UP#1720: ETL chunk from CMS_DEID.bcarrier_claims.
17:38:17 INFO 0:01:15.191470 [1] upload job: <oracle://me@db-server/sgrouse>

"""

from typing import Iterator, List, Tuple
import enum

import cx_ora_fix; cx_ora_fix.patch_version()  # noqa: E702

import luigi
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import sqlalchemy as sqla

from cms_etl import FromCMS, DBAccessTask, BeneIdSurvey
from etl_tasks import LoggedConnection, UploadTarget, make_url, log_plan
from param_val import IntParam
from sql_syntax import Params


class CMSRIFLoad(luigi.WrapperTask):
    def requires(self) -> List[luigi.Task]:
        return [CarrierClaims(),
                OutpatientClaims()]


class DataLoadTask(FromCMS, DBAccessTask):
    @property
    def label(self) -> str:
        raise NotImplementedError

    @property
    def input_label(self) -> str:
        raise NotImplementedError

    def output(self) -> luigi.Target:
        return self._upload_target()

    def _upload_target(self) -> 'UploadTarget':
        return UploadTarget(self._make_url(self.account),
                            self.project.upload_table,
                            self.task_id, self.source,
                            echo=self.echo)

    def run(self) -> None:
        upload = self._upload_target()
        with upload.job(self,
                        label=self.label,
                        user_id=make_url(self.account).username) as conn_id_r:
            lc, upload_id, result = conn_id_r
            fact_table = sqla.Table('observation_fact_%s' % upload_id,
                                    sqla.MetaData(),
                                    *[c.copy() for c in self.project.observation_fact_columns])
            fact_table.create(lc._conn)
            fact_dtype = {c.name: c.type for c in fact_table.columns
                          if not c.name.endswith('_blob')}
            bulk_rows = 0
            obs_fact_chunks = self.obs_data(lc, upload_id)
            while 1:
                with lc.log.step('UP#%(upload_id)d: %(event)s from %(input)s',
                                 dict(event='ETL chunk', upload_id=upload_id,
                                      input=self.input_label)):
                    with lc.log.step('%(event)s',
                                     dict(event='get facts')) as step1:
                        try:
                            obs_fact_chunk, message = next(obs_fact_chunks)
                        except StopIteration:
                            break
                        step1.msg_parts.append(' %(fact_qty)s facts')
                        step1.argobj.update(dict(fact_qty=len(obs_fact_chunk)))
                    with lc.log.step('UP#%(upload_id)d: %(event)s %(rowcount)d rows into %(into)s',
                                     dict(event='bulk insert',
                                          upload_id=upload_id,
                                          into=fact_table.name,
                                          rowcount=len(obs_fact_chunk))) as insert_step:
                        obs_fact_chunk.to_sql(name=fact_table.name,
                                              con=lc._conn,
                                              dtype=fact_dtype,
                                              if_exists='append', index=False)
                        bulk_rows += len(obs_fact_chunk)
                        insert_step.argobj.update(dict(rowsubtotal=bulk_rows))
                        insert_step.msg_parts.append(
                            ' (subtotal: %(rowsubtotal)d)')

                    # report progress via the upload_status table
                    lc.execute(upload.table.update()
                               .where(upload.table.c.upload_id == upload_id)
                               .values(loaded_record=bulk_rows,
                                       message=message))
            result[upload.table.c.loaded_record.name] = bulk_rows

    def obs_data(self, lc: LoggedConnection, upload_id: int) -> Iterator[Tuple[pd.DataFrame, str]]:
        raise NotImplementedError


def read_sql_step(sql: str, lc: LoggedConnection, params: Params) -> pd.DataFrame:
    with lc.log.step('%(event)s %(sql1)s' + ('\n%(params)s' if params else ''),
                     dict(event='read_sql', sql1=str(sql).split('\n')[0], params=params)):
        return pd.read_sql(sql, lc._conn, params=params or {})


class BeneMapped(DataLoadTask):
    def ide_source(self, key_cols: str) -> str:
        source_cd = self.source.source_cd[1:-1]  # strip quotes
        return source_cd + key_cols

    def patient_mapping(self, lc: LoggedConnection,
                        bene_id_first: int, bene_id_last: int,
                        debug_plan: bool=False,
                        key_cols: str='(BENE_ID)') -> pd.DataFrame:
        # TODO: use sqlalchemy API
        q = '''select patient_ide bene_id, patient_num from %(I2B2STAR)s.patient_mapping
        where patient_ide_source = :patient_ide_source
        and patient_ide between :bene_id_first and :bene_id_last
        ''' % dict(I2B2STAR=self.project.star_schema)

        params = dict(patient_ide_source=self.ide_source(key_cols),
                      bene_id_first=bene_id_first,
                      bene_id_last=bene_id_last)  # type: Params
        if debug_plan:
            log_plan(lc, event='patient_mapping', sql=q, params=params)
        return read_sql_step(q, lc, params=params)


class MedparMapped(BeneMapped):
    def encounter_mapping(self, lc: LoggedConnection,
                          bene_id_first: int, bene_id_last: int,
                          key_cols: str='(MEDPAR_ID)',
                          debug_plan: bool=False) -> pd.DataFrame:
        q = '''select encounter_ide medpar_id, encounter_num from %(I2B2STAR)s.encounter_mapping
        where encounter_ide_source = :encounter_ide_source
        and patient_ide between :bene_id_first and :bene_id_last
        ''' % dict(I2B2STAR=self.project.star_schema)

        params = dict(encounter_ide_source=self.ide_source(key_cols),
                      bene_id_first=bene_id_first,
                      bene_id_last=bene_id_last)  # type: Params
        if debug_plan:
            log_plan(lc, event='encounter_mapping', sql=q, params=params)
        return read_sql_step(q, lc, params=params)

    @classmethod
    def fmt_patient_day(cls, df: pd.DataFrame) -> pd.Series:
        return df.start_date.dt.strftime('%Y-%m-%d') + ' ' + df.bene_id

    @classmethod
    def _fallback(cls, df: pd.DataFrame) -> pd.Series:
        # @@TODO: replace hash with something portable between Oracle and python
        return - cls.fmt_patient_day(df).apply(hash).abs()

    def with_mapping(self, lc: LoggedConnection, data: pd.DataFrame) -> pd.DataFrame:
        bene_id_first = data.bene_id.min()
        bene_id_last = data.bene_id.max()

        with lc.log.step('%(event)s %(data_len)d facts',
                         dict(event='mapping', data_len=len(data))) as map_step:
            pmap = self.patient_mapping(lc, bene_id_first, bene_id_last)
            map_step.argobj.update(pmap_len=len(pmap))
            map_step.msg_parts.append(' pmap: %(pmap_len)d')
            obs = data.merge(pmap, on=CMSVariables.bene_id)

            if 'medpar_id' in data.columns.values:
                emap = self.encounter_mapping(lc, bene_id_first, bene_id_last)
                map_step.argobj.update(emap_len=len(emap))
                map_step.msg_parts.append(' emap: %(emap_len)d')
                obs = obs.merge(emap, on=CMSVariables.medpar_id, how='left')
            obs.encounter_num = obs.encounter_num.fillna(self._fallback(obs))

        return obs


class CMSVariables(object):
    i2b2_map = dict(
        patient_ide='bene_id',
        start_date='clm_from_dt',
        end_date='clm_thru_dt',
        update_date='nch_wkly_proc_dt')

    bene_id = 'bene_id',
    medpar_id = 'medpar_id'

    pdx = 'prncpal_dgns_cd'

    """Tables all have less than 10^3 columns."""
    max_cols_digits = 3

    @classmethod
    def column_properties(cls, info: pd.DataFrame,
                          px_pat: str=r'.*prcdr_',
                          dx_pat: str=r'.*(_dgns_|rsn_visit)') -> pd.DataFrame:
        info['valtype_cd'] = [col_valtype(c).value for c in info.column.values]
        info.loc[info.column_name.isin(cls.i2b2_map.values()), 'valtype_cd'] = np.nan
        info['is_px'] = info.column_name.str.match(px_pat)
        info['is_dx'] = info.column_name.str.match(dx_pat)
        return info.drop('column', 1)


def rif_modifier(table_name: str) -> str:
    return 'CMS_RIF:' + table_name.upper()


@enum.unique
class Valtype(enum.Enum):
    coded = '@'
    text = 't'
    date = 'd'
    numeric = 'n'


@enum.unique
class PDX(enum.Enum):
    """cf. PCORNet CDM"""
    primary = '1'
    secondary = '2'


def col_valtype(col: sqla.Column,
                code_max_len: int=7) -> Valtype:
    """Determine valtype_cd based on measurement level
    """
    return (
        Valtype.numeric
        if isinstance(col.type, sqla.types.Numeric) else
        Valtype.date
        if isinstance(col.type, (sqla.types.Date, sqla.types.DateTime)) else
        Valtype.text if (isinstance(col.type, sqla.types.String) and
                         col.type.length > code_max_len) else
        Valtype.coded
    )


def col_groups(col_info: pd.DataFrame,
               suffixes: List[str]) -> pd.DataFrame:
    out = None
    for ix, suffix in enumerate(suffixes):
        cols = col_info[ix::len(suffixes)].reset_index()[['column_name']]
        if out is None:
            out = cols
        else:
            out = out.merge(cols, left_index=True, right_index=True)
    if out is None:
        raise TypeError('no suffixes?')
    out.columns = ['column_name' + s for s in suffixes]
    return out


def fmt_dx_codes(dgns_vrsn: pd.Series, dgns_cd: pd.Series,
                 decimal_pos: int=3) -> pd.Series:
    #   I found null dgns_vrsn e.g. one record with ADMTG_DGNS_CD = V5789
    #   so let's default to the IDC9 case
    scheme = 'ICD' + dgns_vrsn.where(~dgns_vrsn.isnull(), '9')
    decimal = np.where(dgns_cd.str.len() > decimal_pos, '.', '')
    before = dgns_cd.str.slice(stop=decimal_pos)
    after = dgns_cd.str.slice(start=decimal_pos)
    return scheme + ':' + before + decimal + after


class CMSRIFUpload(MedparMapped, CMSVariables):
    bene_id_first = IntParam()
    bene_id_last = IntParam()
    bene_qty = IntParam(significant=False, default=-1)
    group_num = IntParam(significant=False, default=-1)
    group_qty = IntParam(significant=False, default=-1)

    table_name = 'PLACEHOLDER'

    obs_id_vars = ['patient_ide', 'start_date', 'end_date', 'update_date', 'provider_id']
    obs_value_cols = ['update_date', 'start_date', 'end_date']

    @property
    def label(self) -> str:
        return ('%(task_family)s #%(group_num)s of %(group_qty)s;'
                ' %(bene_qty)s bene_ids %(bene_id_first)s...' %
                dict(self.to_str_params(), task_family=self.task_family))

    @property
    def input_label(self) -> str:
        return self.qualified_name

    @property
    def qualified_name(self) -> str:
        return '%s.%s' % (self.source.cms_rif, self.table_name)

    def chunks(self, lc: LoggedConnection,
               chunk_size: int=1000) -> pd.DataFrame:
        params = dict(bene_id_first=self.bene_id_first,
                      bene_id_last=self.bene_id_last)
        meta = self.source.table_details(lc, [self.table_name])
        t = meta.tables[self.qualified_name]
        # ISSUE: order_by(t.c.bene_id)?
        q = (sqla.select([t])
             .where(t.c.bene_id.between(self.bene_id_first, self.bene_id_last)))
        log_plan(lc, event='get chunk', query=q, params=params)
        return pd.read_sql(q, lc._conn, params=params, chunksize=chunk_size)

    def column_data(self, lc: LoggedConnection) -> pd.DataFrame:
        meta = self.source.table_details(lc, [self.table_name])
        t = meta.tables[self.qualified_name]

        return pd.DataFrame([dict(column_name=col.name,
                                  data_type=col.type,
                                  column=col)
                             for col in t.columns])

    def obs_data(self, lc: LoggedConnection, upload_id: int,
                 chunk_size: int=100000) -> Iterator[Tuple[pd.DataFrame, str]]:
        cols = self.column_properties(self.column_data(lc))
        chunks = self.chunks(lc, chunk_size=chunk_size)
        row_subtot = 0
        bene_seen = pd.Series(self.bene_id_first)
        while 1:
            with lc.log.step('UP#%(upload_id)d: %(event)s from %(source_table)s',
                             dict(event='select', upload_id=upload_id,
                                  source_table=self.qualified_name)) as s1:
                try:
                    data = next(chunks)
                except StopIteration:
                    break
                row_subtot += len(data)
                bene_seen = pd.Series(bene_seen.append(data.bene_id).unique())
                s1.argobj.update(dict(bene_pct=round(100.0 * len(bene_seen) / self.bene_qty, 2),
                                      bene_subtot=len(bene_seen),
                                      bene_qty=self.bene_qty,
                                      rows_in=len(data),
                                      subtot_in=row_subtot))
                s1.msg_parts.append(
                    ' + %(rows_in)d rows = %(subtot_in)d'
                    ' for %(bene_subtot)d (%(bene_pct)0.2f%%) of %(bene_qty)d bene_ids')
                message = ''.join(s1.msg_parts) % s1.argobj
            with lc.log.step('%(event)s from %(records)d %(source_table)s records',
                             dict(event='stack diagnoses', records=len(data),
                                  source_table=self.qualified_name)) as stack_step:
                obs_dx = self.dx_data(data, self.table_name, cols)
                stack_step.argobj.update(dict(dx_len=len(obs_dx)))
                stack_step.msg_parts.append(' %(dx_len)d diagnoses')
            mapped = self.with_mapping(lc, obs_dx)
            current_time = pd.read_sql(sqla.select([sqla.func.current_timestamp()]),
                                       lc._conn).iloc[0][0]
            obs_fact = self.with_admin(mapped, upload_id=upload_id, import_date=current_time)
            yield obs_fact, message

    @classmethod
    def _map_cols(cls, obs: pd.DataFrame, i2b2_cols: List[str],
                  required: bool=False) -> pd.DataFrame:
        return obs.rename(columns={cls.i2b2_map[c]: c
                                   for c in i2b2_cols
                                   if (required or c in cls.i2b2_map)})

    @classmethod
    def dx_data(cls, rif_data: pd.DataFrame,
                table_name: str, col_info: pd.DataFrame) -> pd.DataFrame:
        """Combine diagnosis columns i2b2 style
        """
        dx_cols = col_groups(col_info[col_info.is_dx], ['_cd', '_vrsn'])
        obs = obs_stack(rif_data, table_name, dx_cols,
                        id_vars=[cls.i2b2_map[v]
                                 for v in cls.obs_id_vars if v in cls.i2b2_map],
                        value_vars=['dgns_cd', 'dgns_vrsn']).reset_index()
        obs['valtype_cd'] = Valtype.coded.value
        obs['concept_cd'] = fmt_dx_codes(obs.dgns_vrsn, obs.dgns_cd)
        obs = cls._map_cols(obs, cls.obs_value_cols, required=True)
        if 'provider_id' not in obs.columns.values:
            obs['provider_id'] = '@'
        return obs

    @classmethod
    def pivot_valtype(cls, valtype: Valtype, rif_data: pd.DataFrame,
                      table_name: str, col_info: pd.DataFrame) -> pd.DataFrame:
        id_vars = [cls.i2b2_map[v] for v in cls.obs_id_vars if v in cls.i2b2_map]
        ty_cols = list(col_info[col_info.valtype_cd == valtype.value].column_name)
        ty_data = rif_data.reset_index()[id_vars + ty_cols].copy()

        spare_digits = CMSVariables.max_cols_digits
        ty_data['instance_num'] = ty_data.index * (10 ** spare_digits)
        ty_data['modifier_cd'] = rif_modifier(table_name)

        obs = ty_data.melt(id_vars=id_vars + ['instance_num', 'modifier_cd'],
                           var_name='column').dropna(subset=['value'])

        V = Valtype
        obs['valtype_cd'] = valtype.value
        if valtype == V.coded:
            obs['concept_cd'] = obs.column.str.upper() + ':' + obs.value
        else:
            obs['concept_cd'] = obs.column.str.upper() + ':'
            if valtype == V.numeric:
                obs['nval_num'] = obs.value
            elif valtype == V.text:
                obs['tval_char'] = obs.value
            elif valtype == V.date:
                obs['tval_char'] = obs.value.astype('<U') # format yyyy-mm-dd...
            else:
                raise TypeError(valtype)

        if valtype == V.date:
            obs['start_date'] = obs['end_date'] = obs.value
        else:
            obs = cls._map_cols(obs, ['start_date', 'end_date'])

        obs = cls._map_cols(obs, ['update_date'], required=True)
        obs = cls._map_cols(obs, ['provider_id'])

        if 'provider_id' not in obs:
            obs['provider_id'] = '@'

        return obs

    def with_admin(self, mapped: pd.DataFrame,
                   import_date: object, upload_id: int) -> pd.DataFrame:
        obs_fact = mapped[[col.name for col in self.project.observation_fact_columns
                           if col.name in mapped.columns.values]].copy()
        obs_fact['sourcesystem_cd'] = self.source.source_cd[1:-1]  # kludgy
        obs_fact['download_date'] = self.source.download_date
        obs_fact['upload_id'] = upload_id
        obs_fact['import_date'] = import_date
        return obs_fact


def obs_stack(rif_data: pd.DataFrame,
              rif_table_name: str, projections: pd.DataFrame,
              id_vars: List[str], value_vars: List[str]) -> pd.DataFrame:
    '''
    :param projections: columns to project (e.g. diagnosis code and version);
                        order matches value_vars
    :param id_vars: a la pandas.melt
    :param value_vars: a la melt; data column (e.g. dgns_cd) followed by dgns_vrsn etc.
    '''
    rif_data = rif_data.reset_index()  # for instance_num
    spare_digits = CMSVariables.max_cols_digits

    out = None
    for ix, rif_cols in projections.iterrows():
        obs = rif_data[id_vars + list(rif_cols.values)].copy()

        instance_num = obs.index * (10 ** spare_digits) + ix
        obs = obs.set_index(id_vars)
        obs.columns = value_vars  # e.g. icd_dgns_cd11 -> dgns_cd
        obs['instance_num'] = instance_num

        obs = obs.dropna(subset=[value_vars[0]])

        obs['modifier_cd'] = (
            PDX.primary.value if rif_cols.values[0] == CMSVariables.pdx else
            rif_modifier(rif_table_name))

        if out is None:
            out = obs
        else:
            out = out.append(obs)

    if out is None:
        raise TypeError('no projections?')

    return out


class CarrierClaimUpload(CMSRIFUpload):
    table_name = 'bcarrier_claims'

    # see missing Carrier Claim Billing NPI Number #8
    # https://github.com/kumc-bmi/grouse/issues/8
    provider_col = None


class OutpatientClaimUpload(CMSRIFUpload):
    table_name = 'outpatient_base_claims'
    provider_col = 'at_physn_npi'


class _BeneIdGrouped(luigi.WrapperTask):
    group_task = CMSRIFUpload  # abstract

    def requires(self) -> List[luigi.Task]:
        table_name = self.group_task.table_name
        survey = BeneIdSurvey(source_table=table_name)
        results = survey.results()
        if not results:
            return [survey]
        return [self.group_task(group_num=ntile.chunk_num,
                                group_qty=len(results),
                                bene_qty=ntile.chunk_size,
                                bene_id_first=ntile.bene_id_first,
                                bene_id_last=ntile.bene_id_last)
                for ntile in results]


class CarrierClaims(_BeneIdGrouped):
    group_task = CarrierClaimUpload


class OutpatientClaims(_BeneIdGrouped):
    group_task = OutpatientClaimUpload
