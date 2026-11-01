extern "C" void func_60c214d8(char *p)
{
    *reinterpret_cast<volatile unsigned char *>(p + 0xe0) = 0;
    *reinterpret_cast<volatile unsigned int *>(p + 0x1f4) = 0x7f7fffff;
    *reinterpret_cast<volatile unsigned int *>(p + 0x1b4) = 0x7f7fffff;
    *reinterpret_cast<volatile unsigned int *>(p + 0x1b8) = 0x7f7fffff;
    *reinterpret_cast<volatile unsigned char *>(p + 0x1f8) = 0;
    *reinterpret_cast<volatile unsigned char *>(p + 0x204) = 0;
    *reinterpret_cast<volatile unsigned char *>(p + 0x206) = 0;
}