extern "C" void func_6026fde8(char *p, unsigned arg);

extern "C" void func_602776b4(char *p, unsigned idx)
{
    if (idx > 3)
        return;
    char *q = p + idx * 0x560 + 0x5dc;
    func_6026fde8(q, 0);
}