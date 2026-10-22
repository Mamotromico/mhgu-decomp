struct func_605159e0_struct {
    unsigned char pad[0x184];
    unsigned char field;
};

extern "C" int func_605159e0(const func_605159e0_struct *p) {
    int result = 0;
    if (p->field > 3) {
        result = 1;
    }
    return result;
}