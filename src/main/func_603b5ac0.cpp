extern "C" int func_603b5ac0(int unused, unsigned x)
{
    unsigned a = x >> 5;
    unsigned hi = (unsigned)(((unsigned long long)a * 0x0A7C5AC5u) >> 32);
    unsigned b = hi >> 7;
    unsigned q = (unsigned)(((unsigned long long)b * 0xCCCCCCCDu) >> 32) >> 3;
    return (int)(b - q * 10);
}