struct S {
    unsigned char pad[0x48];
    int *data;
};

extern "C" int func_60c7188c(const struct S *s, int i)
{
    return s->data[i];
}