create database OCR;
use OCR;
create table Placas(
placa varchar(7) primary key not null,
dono_do_veiculo varchar(50) not null,
telefone varchar(11) not null,
cargo varchar(50)
);

insert into placas (placa, dono_do_veiculo, telefone) values ("FBI5551", "lucas costa", "91992415502");
insert into placas (placa, dono_do_veiculo, telefone) values ("DQE2H66", "Gustavo Nascimento", "19999547856");
insert into placas (placa, dono_do_veiculo, telefone) values ("FBI5551", "wandrel alves", "19987541618");