extern "C" void func_6130a804(void *);

struct S {
    void *f0;          // +0x00 (4 bytes)
    unsigned f4;       // +0x04 (4 bytes)
    char pad8[0x24 - 0x08];
    char f24;          // +0x24 ... (address passed to callee)
    char pad25[0x30 - 0x25];
    unsigned char f30; // +0x30 (1 byte)
};

extern "C" void func_613a0900(S *s)
{
    s->f4 = 0;
    func_6130a804(&s->f24);
    s->f30 = 0;
    s->f0 = 0;
}