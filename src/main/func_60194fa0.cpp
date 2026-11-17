extern "C" void func_60194fa0(unsigned base, unsigned idx)
{
    unsigned char *p = (unsigned char *)(base + (idx << 8)) + 0x214;
    unsigned char v = *p;
    *p = (v & 1) ? (unsigned char)(v & 0xfe) : (unsigned char)(v | 1);
}