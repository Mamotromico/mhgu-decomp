struct S_605d5160 {
    unsigned char pad[0x50];
    unsigned int field;
};

extern "C" int func_605d5160(S_605d5160* p) {
    return p->field == 1;
}