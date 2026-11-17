extern "C" unsigned char *func_601e2eec(unsigned char *);

extern "C" unsigned char *func_603bd294(char *p)
{
    unsigned char *r = *(unsigned char **)(p + 0xd84);
    if (r == 0)
        return 0;
    return func_601e2eec(r);
}