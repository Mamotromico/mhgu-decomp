struct S {
    unsigned char _pad[0x5d8];
    unsigned char _bit0 : 1;
    unsigned char _bit1 : 1;
};

extern "C" unsigned int func_6130e490(const struct S *s) {
    return s->_bit1;
}