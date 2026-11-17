extern "C" void func_60c46c4c(char *p, int idx, char val)
{
    if (idx != -1) {
        unsigned n = *(unsigned *)(p + 0xbc);
        if (n > (unsigned)idx) {
            char **q = *(char ***)(p + 0xc8);
            char *e = q[idx];
            if (e != 0)
                *(char *)(e + 5) = val;
        }
    }
}