extern "C" void func_607bd990(void *, const void *, unsigned);

extern "C" void func_601cabac(char *base, unsigned idx, const void *src)
{
    if (idx > 0x1a)
        return;
    char *dst = base + idx * 0x68 + 0x1d40;
    func_607bd990(dst, src, 0x68);
}