struct Block {
    unsigned char pad[0x10];
    unsigned int field;
};

extern "C" int func_607ca56c(Block *p) {
    return p->field == 0;
}