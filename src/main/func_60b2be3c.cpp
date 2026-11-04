extern "C" void func_60b2be3c(char *p, unsigned v)
{
    unsigned *q = (unsigned *)(p + 0x18);
    for (int i = 0; i < 16; i++) {
        if (q[i] == v)
            q[i] = 0;
    }
}