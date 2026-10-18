struct S {
    unsigned char pad[0x5DA];
    unsigned char flags;
};

extern "C" int func_6130e6ac(const struct S *p) {
    return (p->flags >> 2) & 1;
}