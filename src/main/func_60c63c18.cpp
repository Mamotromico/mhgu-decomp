extern "C" void func_60c63c18(char *p, unsigned v)
{
    if (v == 0) {
        v = 1;
        *(unsigned *)(p + 0x40) = v;
        return;
    }
    unsigned cur = *(unsigned *)(p + 0x40);
    if (cur > 4)
        v = 4;
    *(unsigned *)(p + 0x40) = v;
}