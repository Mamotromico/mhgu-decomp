extern "C" void func_60898ac0(void);

extern "C" void func_6001c334(void) __attribute__((naked));

extern "C" void func_6001c334(void)
{
    __asm__ volatile("b func_60898ac0");
}