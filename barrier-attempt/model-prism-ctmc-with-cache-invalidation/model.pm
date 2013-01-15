ctmc

const me_1 = 1; //index
const me_2 = 2;

const me_bit_1 = 1; //2^0
const me_bit_2 = 2; //2^1

const empty = 0;
const full = me_bit_1 + me_bit_2;

const min_invalid = empty - 1;
const max_invalid = full + 1;


global entry : [min_invalid..max_invalid] init empty;
global exit : [min_invalid..max_invalid] init empty;
global left : bool init false;



formula base_rate  = 2500.0;
formula tick       = base_rate / 1.0;
formula work       = base_rate / 1000.0;
formula read       = base_rate / 50.0;
formula write      = base_rate / 100.0;



module process_1
	l_1 : [0..17] init 0;
	cp_1 : [min_invalid..max_invalid] init empty;

	[] l_1=0 -> read : (l_1'=1) & (cp_1'=entry);

	[] l_1=1 & mod(floor(cp_1/me_bit_1),2)=1 -> tick : (l_1'=3);
	[] l_1=1 & mod(floor(cp_1/me_bit_1),2)=0 -> write : (l_1'=3) & (entry'=min(max_invalid,max(cp_1+me_bit_1, min_invalid)));

	[] l_1=3 & (  cp_1 != full & left = false ) -> read : (l_1'=0);
	[] l_1=3 & (!(cp_1 != full & left = false)) -> read : (l_1'=4);
	[] l_1=4 -> write : (l_1'=6) & (exit'=empty);
	[] l_1=6 -> write : (l_1'=8) & (left'=true);


	[] l_1=8 -> work : (l_1'=9);


	[] l_1=9 -> read : (l_1'=10) & (cp_1'=exit);

	[] l_1=10 & mod(floor(cp_1/me_bit_1),2)=1 -> tick : (l_1'=12);
	[] l_1=10 & mod(floor(cp_1/me_bit_1),2)=0 -> write : (l_1'=12) & (exit'=min(max_invalid,max(cp_1+me_bit_1, min_invalid)));

	[] l_1=12 & (  cp_1 != full & left = true ) -> read : (l_1'=9);
	[] l_1=12 & (!(cp_1 != full & left = true)) -> read : (l_1'=13);
	[] l_1=13 -> write : (l_1'=15) & (entry'=empty);
	[] l_1=15 -> write : (l_1'=17) & (left'=false);


	[] l_1=17 -> work : (l_1'=0);

endmodule


const modified = 0;
const shared = 1;
const invalid = 2;

module cacheline_1
	m_1 : [0..2] init invalid;
	
	[write_2] true         -> (m_1'=invalid);

	[read_2]  m_1=invalid  -> (m_1'=invalid);
	[read_1]  m_1=invalid  -> (m_1'=shared);
	[write_1] m_1=invalid  -> (m_1'=modified);


	[read_2]  m_1=shared   -> (m_1'=shared);
	[read_1]  m_1=shared   -> (m_1'=shared);
	[write_1] m_1=shared   -> (m_1'=modified);

	[read_2]  m_1=modified -> (m_1'=shared);
	[read_1]  m_1=modified -> (m_1'=modified);
	[write_1] m_1=modified -> (m_1'=modified);
endmodule


module process_2 = process_1 [
	me_1     =me_2,
	me_bit_1 =me_bit_2,
	l_1      =l_2,
	cp_1     =cp_2
] endmodule

module cacheline_2 = cacheline_1 [
	m_1=m_2,
	read_1=read_2,
	read_2=read_1,
	write_1=write_2,
	write_2=write_1
] endmodule

