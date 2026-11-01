extern "C" int func_6027c9d8(void *p)
{
    char *base = (char *)p;
    float *f = (float *)(base + 0x1464);
    if (*f > 0.0f)
        return 1;
    int v = *(int *)(base + 0x1470);
    return v != 0 ? 1 : 0;
}