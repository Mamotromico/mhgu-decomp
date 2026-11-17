extern "C" {
void *func_6053985c(void *p, int n);
extern char D_6176ad44[];
}

extern "C" void func_6051c4cc(char *p)
{
    char *r = (char *)func_6053985c(p, 9);
    *(char **)r = &D_6176ad44[8];
}