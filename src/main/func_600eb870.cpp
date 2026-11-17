extern "C" void func_600eb870(unsigned char *self, unsigned int *arg) {
    unsigned int *p = *(unsigned int **)arg;
    unsigned int (*fn)(unsigned int *) = *(unsigned int (**)(unsigned int *))(p + 3);
    unsigned int r = fn(arg);
    *(unsigned int *)(self + 4) = r;
}