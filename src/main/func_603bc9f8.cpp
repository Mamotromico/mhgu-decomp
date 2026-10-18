struct func_603bc9f8_s {
    unsigned char pad[0x38];
    unsigned short v[0x100];
};

extern "C" unsigned short func_603bc9f8(const struct func_603bc9f8_s *p, int i) {
    return p->v[i];
}