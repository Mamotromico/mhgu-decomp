struct func_603aecc0_data {
    unsigned char pad[0xb8];
    unsigned int flags;
};

extern "C" int func_603aecc0(func_603aecc0_data *p) {
    return (p->flags & 0x10400u) == 0x10400u;
}