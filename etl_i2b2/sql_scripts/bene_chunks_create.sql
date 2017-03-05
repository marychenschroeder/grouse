create table bene_chunks (
        bene_id_source varchar2(80) not null,
        chunk_qty integer not null,
        chunk_num integer not null,
        chunk_size integer not null,
        bene_id_first varchar2(64) not null,
        bene_id_last varchar2(64) not null,
        constraint bene_chunks_pk primary key (bene_id_source, chunk_qty, chunk_num),
        constraint chunk_qty_pos check (chunk_qty > 0),
        constraint chunk_num_in_range check (chunk_num between 1 and chunk_qty),
        constraint chunk_size_pos check (chunk_size > 0)
        );

-- Can we refer to the table without error?
select coalesce((select 1 from bene_chunks where rownum=1), 1) complete
from dual;
