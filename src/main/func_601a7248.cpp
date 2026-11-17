extern "C" {

extern char D_61897f78[];

int func_601a7248(void)
{
    char **p = (char **)&D_61897f78;
    unsigned char v = *(unsigned char *)(*p + 0x958);
    return (v >> 5) & 1;
}

}