extern "C" void func_6005d4fc(int, int);

extern "C" void func_6005d754(int a, int b)
{
    func_6005d4fc(a, *(int *)(a + b * 4 + 0x1c));
}