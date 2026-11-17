extern "C" void func_609f552c(void *);

extern "C" void func_609dcd88(unsigned char *p)
{
    unsigned *field = (unsigned *)(p + 0x64);
    unsigned v = *field;
    if (v != 0) {
        unsigned flags = *(unsigned *)(v + 0xc) & 0x7;
        flags = flags - 1;
        if (flags >= 2) {
            flags = 0;
            *field = flags;
        }
    }
    func_609f552c(p);
}