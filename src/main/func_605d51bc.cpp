struct Data605d51bc {
    unsigned char pad[0x50];
    unsigned int field;
};

extern "C" int func_605d51bc(Data605d51bc *p) {
    return p->field == 2 ? 1 : 0;
}