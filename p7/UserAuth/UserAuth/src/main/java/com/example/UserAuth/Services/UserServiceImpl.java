package com.example.UserAuth.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.example.UserAuth.*;
import com.example.UserAuth.Entity.User;
import com.example.UserAuth.dto.UserDto;
import com.example.UserAuth.repositories.UserRepository;

@Service
public class UserServiceImpl implements UserService {

 @Autowired
 PasswordEncoder passwordEncoder;

 private UserRepository userRepository;

 public UserServiceImpl(UserRepository userRepository) {
  super();
  this.userRepository = userRepository;
 }

 @Override
 public User findByUsername(String username) {
  return userRepository.findByUsername(username);
 }

 @Override
 public User save(UserDto userDto) {
  User user = new User(userDto.getUsername(), passwordEncoder.encode(userDto.getPassword()),
    userDto.getFullname());
  return userRepository.save(user);
 }

}