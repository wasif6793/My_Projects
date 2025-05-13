package com.example.UserAuth.Controller;

import java.security.Principal;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

import com.example.UserAuth.Entity.User;
import com.example.UserAuth.Services.UserService;
import com.example.UserAuth.dto.UserDto;

@Controller
public class UserController {

 @Autowired
 private UserDetailsService userDetailsService;

 private UserService userService;

 public UserController(UserService userService) {
  this.userService = userService;
 }

 @GetMapping("/home")
 public String home(Model model, Principal principal) {
  // Get the username of the logged-in user
  String username = principal.getName();

  // Pass username to the Streamlit app via the URL
  String streamlitUrl = "http://localhost:8501/?username=" + username; // Modify URL if Streamlit is hosted differently

  // Redirect to Streamlit app
  return "redirect:" + streamlitUrl;
 }

 @GetMapping("/login")
 public String login(Model model, UserDto userDto) {

  model.addAttribute("user", userDto);
  return "login";
 }

 @GetMapping("/register")
 public String register(Model model, UserDto userDto) {
  model.addAttribute("user", userDto);
  return "register";
 }

 @PostMapping("/register")
 public String registerSava(@ModelAttribute("user") UserDto userDto, Model model) {
  User user = userService.findByUsername(userDto.getUsername());
  if (user != null) {
   model.addAttribute("Userexist", user);
   return "register";
  }
  userService.save(userDto);
  return "redirect:/register?success";
 }
}