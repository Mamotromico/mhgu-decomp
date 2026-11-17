extern "C" char *func_60ba2c00(char *out, char *p, int key)
{
    unsigned v = *(unsigned *)p;
    out = 0;
    goto test;
    for (;;) {
        p = p + 0xc;
        v = *(unsigned *)p;
test:
        if (v == 0)
            return out;
        if (v != (unsigned)key)
            continue;
        return p;
    }
}