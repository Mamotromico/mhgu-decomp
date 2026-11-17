extern "C" { void func_612cab5c(void *, unsigned, unsigned *); }

extern "C" void func_612c8900(char *p, unsigned a, unsigned b)
{
    unsigned t = b;
    func_612cab5c(p + 0xd0, a, &t);
}