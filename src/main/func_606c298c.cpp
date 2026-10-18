struct func_606c298c_obj {
    unsigned char pad[0x18f8];
    unsigned int value;
};

extern "C" void func_606c298c(struct func_606c298c_obj *obj, unsigned int value)
{
    obj->value = value;
}