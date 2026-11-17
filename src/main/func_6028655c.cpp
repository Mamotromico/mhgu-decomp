extern "C" {
int func_600df814(char *, int);
}

extern "C" int func_6028655c(char *p)
{
    char *q = *(char **)(p + 0x13c4);
    char *r = (char *)func_600df814(q + 4, 0);
    unsigned char b = *(unsigned char *)(r + 0x10);
    return (b >> 2) & 1;
}