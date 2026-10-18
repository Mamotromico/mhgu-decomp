struct func_60c184a0_obj {
    char pad[4];
    int value;
};

extern "C" int func_60c184a0(struct func_60c184a0_obj *obj, int value)
{
    obj->value = value;
    return 1;
}