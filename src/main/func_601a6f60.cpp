extern "C" void func_601a6f80(void *);

extern "C" void func_601a6f60(unsigned char *p)
{
    func_601a6f80(p);
    unsigned v = *(unsigned *)(p + 0x128);
    v = (v & ~(3u << 9)) | (1u << 9);
    *(unsigned *)(p + 0x128) = v;
}